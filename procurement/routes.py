import logging

import requests
from flask import Blueprint, current_app, jsonify, request
from db import db

from message_queue.cache import (
    cache_entity,
    cache_list,
    get_cached_entity,
    get_cached_list,
)

from config import Config
from models import Procurements

logger = logging.getLogger(__name__)

bp = Blueprint("procurement", __name__)


@bp.route("/health", methods=["GET"])
def health_check():
    app = current_app
    consumer_running = (
        getattr(app, "supervisor", None) and len(app.supervisor.supervisors) > 0
    )
    return jsonify(
        {
            "status": "healthy",
            "service": Config.SERVICE_NAME,
            "cache_warmed": getattr(app, "cache_warmed", False),
            "consumer_running": bool(consumer_running),
            "supplier_breaker": app.supplier_breaker.get_state(),
            "product_breaker": app.product_breaker.get_state(),
        }
    ), 200


@bp.route("/procurements", methods=["GET"])
def get_procurements():
    try:
        start = request.args.get("start", 0, type=int)
        limit = request.args.get("limit", 50, type=int)

        # Check cache first
        cache_key = f"page_{start}_limit_{limit}"
        cached = get_cached_list("procurement", cache_key)
        if cached:
            return jsonify(
                {
                    "procurements": cached,
                    "start": start,
                    "limit": limit,
                    "count": len(cached),
                    "cached": True,
                }
            ), 200

        transactions = Procurements.query.offset(start).limit(limit).all()

        # Enrich with supplier and product data
        result = []
        for t in transactions:
            tx_dict = t.to_dict()

            if t.supplier_id:
                supplier = fetch_entity_with_breaker(
                    "supplier",
                    t.supplier_id,
                    Config.SUPPLIER_SERVICE_URL,
                    current_app.supplier_breaker,
                )
                if supplier:
                    tx_dict["supplier"] = supplier

            if t.product_id:
                product = fetch_entity_with_breaker(
                    "product",
                    t.product_id,
                    Config.PRODUCT_SERVICE_URL,
                    current_app.product_breaker,
                )
                if product:
                    tx_dict["product"] = product

            # Cache individual enriched record
            cache_entity("procurement", t.id, tx_dict, ttl=3600)
            result.append(tx_dict)

        # Cache the list
        cache_list("procurement", cache_key, result, ttl=3600)

        return jsonify(
            {
                "procurements": result,
                "start": start,
                "limit": limit,
                "count": len(result),
            }
        ), 200
    except Exception as e:
        logger.error(f"Error getting procurements: {e}")
        return jsonify({"error": "Failed to fetch procurements"}), 500


@bp.route("/procurements", methods=["POST"])
def create_procurement():
    try:
        data = request.get_json()

        if not data.get("supplier_id") or not data.get("product_id"):
            return jsonify({"error": "supplier_id and product_id are required"}), 400

        # Fetch supplier and product data for denormalization
        supplier = fetch_entity_with_breaker(
            "supplier",
            data["supplier_id"],
            Config.SUPPLIER_SERVICE_URL,
            current_app.supplier_breaker,
        )
        product = fetch_entity_with_breaker(
            "product",
            data["product_id"],
            Config.PRODUCT_SERVICE_URL,
            current_app.product_breaker,
        )

        if not supplier or not product:
            return jsonify({"error": "Invalid supplier_id or product_id"}), 400

        quantity = data.get("quantity", 0)
        unit_price = product.get("price_buy", 0)

        # Create normalized procurement record
        transaction = Procurements(
            supplier_id=data["supplier_id"],
            product_id=data["product_id"],
            quantity=quantity,
            total_cost=quantity * unit_price,
        )

        db.session.add(transaction)
        db.session.commit()

        # Publish stock-in event to inventory service
        event_publisher = getattr(current_app, "event_publisher", None)
        if event_publisher:
            event_publisher.publish(
                "procurement_stock_in",
                "stock_in",
                transaction.id,
                {
                    "product_id": transaction.product_id,
                    "quantity": transaction.quantity,
                },
            )

        logger.info(
            f"Procurement created: ID {transaction.id}, product {transaction.product_id}, qty {transaction.quantity}"
        )

        return jsonify(
            transaction.to_dict(
                include_relations=True, supplier_data=supplier, product_data=product
            )
        ), 201

    except Exception as e:
        logger.error(f"Error creating procurement: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create procurement"}), 500


@bp.route("/procurements/product/<int:product_id>", methods=["GET"])
def get_procurements_by_product(product_id):
    try:
        transactions = Procurements.query.filter_by(product_id=product_id).all()
        return jsonify(
            {
                "procurements": [t.to_dict() for t in transactions],
                "product_id": product_id,
                "count": len(transactions),
            }
        ), 200
    except Exception as e:
        logger.error(f"Error getting procurements by product: {e}")
        return jsonify({"error": "Failed to fetch procurements"}), 500


@bp.route("/procurements/supplier/<int:supplier_id>", methods=["GET"])
def get_procurements_by_supplier(supplier_id):
    try:
        transactions = Procurements.query.filter_by(supplier_id=supplier_id).all()
        return jsonify(
            {
                "procurements": [t.to_dict() for t in transactions],
                "supplier_id": supplier_id,
                "count": len(transactions),
            }
        ), 200
    except Exception as e:
        logger.error(f"Error getting procurements by supplier: {e}")
        return jsonify({"error": "Failed to fetch procurements"}), 500


# Utility used by the routes
def fetch_entity_with_breaker(entity_type, entity_id, service_url, breaker):
    """Fetch entity from cache or service with circuit breaker"""
    cached = get_cached_entity(entity_type, entity_id)
    if cached:
        return cached

    def fetch():
        response = requests.get(f"{service_url}/{entity_type}s/{entity_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None

    try:
        entity = breaker.call(fetch)
        if entity:
            cache_entity(entity_type, entity_id, entity, ttl=86400)
        return entity
    except Exception as e:
        logger.error(f"Failed to fetch {entity_type} {entity_id}: {e}")
        return None

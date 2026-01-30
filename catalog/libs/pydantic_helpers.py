from typing import List, Type, TypeVar
from pydantic import BaseModel, ValidationError
from flask import jsonify

T = TypeVar('T', bound=BaseModel)


def serialize_model(model_instance, schema: Type[T]) -> dict:
    """Convert SQLAlchemy model to Pydantic schema dict"""
    return schema.model_validate(model_instance).model_dump(mode='json')


def serialize_models(model_instances: List, schema: Type[T]) -> List[dict]:
    """Convert list of SQLAlchemy models to list of Pydantic schema dicts"""
    return [schema.model_validate(instance).model_dump(mode='json') for instance in model_instances]


def validate_request_data(data: dict, schema: Type[T]) -> T:
    """Validate request data against Pydantic schema"""
    return schema.model_validate(data)


def handle_validation_error(err: ValidationError):
    """Format Pydantic validation errors for Flask response"""
    return jsonify({"errors": err.errors()}), 400

#!/bin/bash

# Docker run script for Flask Inventory Microservices
# Usage: ./dockerrun.sh [up|down|restart|logs|status] [options]

case "$1" in
    up)
        if [ "$2" = "--build" ]; then
            echo "Building and starting all services..."
            docker compose up --build -d
        else
            echo "Starting all services..."
            docker compose up -d
        fi
        ;;
    down)
        echo "Stopping all services..."
        docker compose down
        ;;
    restart)
        echo "Restarting all services..."
        docker compose restart
        ;;
    logs)
        if [ -n "$2" ]; then
            docker compose logs -f "$2"
        else
            docker compose logs -f
        fi
        ;;
    status)
        docker compose ps
        ;;
    clean)
        echo "Stopping services and removing volumes..."
        docker compose down -v
        ;;
    *)
        echo "Usage: $0 {up|down|restart|logs|status|clean} [options]"
        echo ""
        echo "Commands:"
        echo "  up          Start all services"
        echo "  up --build  Build and start all services"
        echo "  down        Stop all services"
        echo "  restart     Restart all services"
        echo "  logs        View logs (optionally specify service name)"
        echo "  status      Show status of all services"
        echo "  clean       Stop services and remove volumes"
        exit 1
        ;;
esac
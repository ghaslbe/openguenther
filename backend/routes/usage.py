from flask import Blueprint, request, jsonify
from models import get_usage_stats, get_usage_timeline, reset_usage_stats

usage_bp = Blueprint('usage', __name__)


@usage_bp.route('/api/usage/stats', methods=['GET'])
def stats():
    period = request.args.get('period', 'today')  # today|week|month|all
    return jsonify(get_usage_stats(period))


@usage_bp.route('/api/usage/timeline', methods=['GET'])
def timeline():
    granularity = request.args.get('granularity', 'day')  # hour|day|month
    return jsonify(get_usage_timeline(granularity))


@usage_bp.route('/api/usage/stats', methods=['DELETE'])
def reset():
    reset_usage_stats()
    return jsonify({'success': True})

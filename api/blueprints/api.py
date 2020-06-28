import math
from flask import Blueprint, request, jsonify
from elasticsearch import Elasticsearch
import certifi
import json
import random

from .auth import login_required, admin_required

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    jwt_refresh_token_required, create_refresh_token,
    get_jwt_identity, set_access_cookies,
    set_refresh_cookies, unset_jwt_cookies
)

from util.elasticsearch_queries import (
    or_contains_filter, or_not_contains_filter,
    and_filter, search_query, 
    add_tags_query, remove_tags_query
)

api = Blueprint('api', __name__)

with open('./api/config/config.json') as f:
    config = json.load(f)
    es = Elasticsearch(
        [config.get("ELASTICSEARCH_URL")], 
        use_ssl=True, 
        ca_certs=certifi.where()
    )



@api.route("/search", methods=["POST"])
@login_required
def api_index():
    req = request.get_json()
    and_filters = []
    and_not_filters = []
    or_filters = []

    for filter in req['filters']:
        if req['isOr']:
            if filter['filter'] == "contains":
                or_filters.append(or_contains_filter(filter))
            elif filter['filter'] == "contains_not":
                or_filters.append(or_not_contains_filter(filter))
            else:
                print("Unsupported filter type %s" % filter['filter'])

        if not req['isOr']:
            if filter['filter'] == "contains":
                and_filters.append(and_filter(filter))
            elif filter['filter'] == "contains_not":
                and_not_filters.append(and_filter(filter))
            else:
                print("Unsupported filter type %s" % filter['filter'])

    query = search_query(req, and_filters, and_not_filters, or_filters)
    res = es.search(index=config.get("ELASTICSEARCH_INDEX"), body=query)
    return res


@api.route("/resource/<string:id>", methods=["GET"])
@login_required
def resource(id):
    query = {
        "query": {
            "match": {
                "_id": id
            }
        }
    }
    res = es.search(index=config.get("ELASTICSEARCH_INDEX"), body=query)
    return res


@api.route("/tags/add", methods = ["POST"])
@login_required
def add_tags():
    req = request.get_json()

    tag_type = req.get("tagType")
    tag_value = req.get("tagValue")
    resource_id = req.get("resourceId")

    if tag_type not in ["locations", "people", "orgs", "other"] or tag_value is "":
        return jsonify({
            "msg": "Please fill out all fields" 
        }), 400

    res = es.update(index=config.get("ELASTICSEARCH_INDEX"), id=resource_id, body=add_tags_query(tag_type, tag_value), refresh=True)

    return jsonify({
        "added": True
    }), 200


@api.route("/tags/remove", methods = ["POST"])
@admin_required
def remove_tags():
    req = request.get_json()

    tag_type = req.get("tagType")
    tag_value = req.get("tagValue")
    resource_id = req.get("resourceId")

    if tag_type not in ["locations", "people", "orgs", "other"] or tag_value is "":
        return jsonify({
            "msg": "Unknown error" 
        }), 400

    res = es.update(index=config.get("ELASTICSEARCH_INDEX"), id=resource_id, body=remove_tags_query(tag_type, tag_value), refresh=True)
    return jsonify({
        "removed": True
    }), 200


@api.route("/graph_neighbors", methods=["POST"])
@login_required
def graph_neighbors():
    req = request.get_json()
    query = req.get('query')
    # Randomly select root if none provided
    if query == None:
        query = str(random.random())

    neighbors = [{"id": query, "depth": 0, "angle": 0}]
    links = []

    children_per_layer = {
        1: 5,
        2: 3
    }

    def expand_neighbors(neighbors, links, last_layer, i):
        new_neighbors = []
        for neighbor in last_layer:
            relevant = [str(random.random()) for i in range(children_per_layer[i+1])]
            for r in relevant:
                if r not in [n["id"] for n in neighbors] and r not in [n["id"] for n in new_neighbors]:
                    links.append({"source": neighbor["id"], "target": r, "length": 1.0/(i+1)})
                    new_neighbors.append({"id": r, "depth": i+1 })
        for i in range(len(new_neighbors)):
            new_neighbors[i]['angle'] = 2.0 * math.pi * i / len(new_neighbors) 
        neighbors += new_neighbors
        return new_neighbors

    ITERATIONS = 2

    global new_neighbors    
    new_neighbors = neighbors
    for i in range(ITERATIONS):
        new_neighbors = expand_neighbors(neighbors, links, new_neighbors, i)
        
    return {
        "nodes": neighbors,
        "links": links,
        "root": query
    }


@api.route("/tags/suggestions", methods=["POST"])
@login_required
def suggested_tags():
    req = request.get_json()
    query = {
        "query": {
            "prefix": {
                "tags.%s" % req["type"]: {
                    "value": req["query"].lower()
                }
            }
        },
        "aggs": {
            "suggested_tags": {
                "terms": {
                    "field": "tags.%s.keyword" % req["type"],
                    "size": 1000
                }
            }
        },
        "size": 0
    }

    res = es.search(index=config.get("ELASTICSEARCH_INDEX"), body=query)
    buckets = res["aggregations"]["suggested_tags"]["buckets"]
    all_tags = [bucket["key"] for bucket in buckets]
    tags = list(filter( lambda tag : tag.lower().startswith(req["query"].lower()), all_tags))[0:25]
    return {
        "tags": tags
    }
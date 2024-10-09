from config import ES_INDEX, es
from typing import Dict, List, Tuple, Optional, Any
import statistics
from dateutil.parser import parse
import math

async def create_index() -> None:
    await es.options(ignore_status=[400]).indices.create(
        index=ES_INDEX,
        body={
            "mappings": {
                "properties": {
                    "user_id": {"type": "keyword"},
                    "username": {"type": "text"},
                    "date_first": {"type": "date"},
                    "date_last": {"type": "date"},
                    "count": {"type": "integer"},
                    "ip": {"type": "ip"},
                    "user_agent": {"type": "text"},
                    "isp": {"type": "text"},
                    "country": {"type": "keyword"},
                    "region": {"type": "keyword"},
                }
            }
        },
    )
    print("🗂️ Index created or already exists.")


async def standard_search(
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: str = "date_last",
    page: int = 1,
    size: int = 10,
) -> Tuple[List[Dict[str, Any]], int]:
    query: Dict[str, Any] = {"bool": {"must": []}}
    if user_id:
        query["bool"]["must"].append({"term": {"user_id": user_id}})
    if ip_address:
        query["bool"]["must"].append({"term": {"ip": ip_address}})
    if start_date and end_date:
        query["bool"]["must"].append(
            {"range": {"date_last": {"gte": start_date, "lte": end_date}}}
        )

    start: int = (page - 1) * size
    try:
        response = await es.search(
            index=ES_INDEX,
            body={
                "query": query,
                "sort": [{sort_by: {"order": "desc"}}],
                "from": start,
                "size": size,
            },
        )
        return response["hits"]["hits"], response["hits"]["total"]["value"]
    except Exception as e:
        return [{"error": f"⚠️ Error querying Elasticsearch: {str(e)}"}], 0


async def fetch_unique(
    term_field: str,
    term_value: Optional[str],
    agg_field: str,
    date_field: str = "date_last",
    page: int = 1,
    size: int = 10,
) -> Tuple[List[Dict[str, Any]], int]:
    if not term_value:
        return [
            {
                "error": f"{term_field.replace('_', ' ').title()} is required for this search"
            }
        ], 0

    aggs: Dict[str, Any] = {
        "composite_aggs": {
            "composite": {
                "sources": [
                    {f"unique_{agg_field}": {"terms": {"field": agg_field}}},
                    {"date_last": {"terms": {"field": date_field}}},
                ],
                "size": size,
            }
        }
    }
    all_terms: List[Dict[str, Any]] = []
    start_after: Optional[Dict[str, Any]] = None

    try:
        while True:
            if start_after:
                aggs["composite_aggs"]["composite"]["after"] = start_after

            response = await es.search(
                index=ES_INDEX,
                body={
                    "query": {"term": {term_field: term_value}},
                    "aggs": aggs,
                    "size": 0,
                },
            )

            buckets = response["aggregations"]["composite_aggs"]["buckets"]
            if not buckets:
                break

            all_terms.extend(
                [
                    {
                        agg_field: bucket["key"][f"unique_{agg_field}"],
                        "date_last": bucket["key"][date_field],
                    }
                    for bucket in buckets
                ]
            )
            if len(buckets) < size:
                break
            start_after = buckets[-1]["key"]

        all_terms.sort(key=lambda x: x["date_last"], reverse=True)
        unique_terms: Dict[Any, str] = {
            term[agg_field]: term["date_last"] for term in all_terms
        }

        unique_term_list: List[Tuple[Any, str]] = list(unique_terms.items())
        paginated_terms: List[Tuple[Any, str]] = unique_term_list[
            (page - 1) * size : page * size
        ]
        return [{agg_field: term} for term, _ in paginated_terms], len(unique_term_list)

    except Exception as e:
        return [{"error": f"⚠️ Error querying Elasticsearch: {str(e)}"}], 0


async def unique_user_search(
    ip_address: Optional[str] = None, page: int = 1, size: int = 10
) -> Tuple[List[Dict[str, Any]], int]:
    return await fetch_unique("ip", ip_address, "user_id", page=page, size=size)


async def unique_ip_search(
    user_id: Optional[str] = None, page: int = 1, size: int = 10
) -> Tuple[List[Dict[str, Any]], int]:
    return await fetch_unique("user_id", user_id, "ip", page=page, size=size)


async def find_alts(user_id: str, confidence_threshold: float = 0.5) -> List[Dict[str, Any]]:
    user_ips, _ = await unique_ip_search(user_id=user_id, size=1000)
    
    potential_alts = []
    
    for ip_entry in user_ips:
        ip = ip_entry['ip']
        other_users, _ = await unique_user_search(ip_address=ip, size=1000)
        
        for other_user in other_users:
            if other_user['user_id'] != user_id:
                user_details, _ = await standard_search(user_id=user_id, ip_address=ip, size=1000)
                other_user_details, _ = await standard_search(user_id=other_user['user_id'], ip_address=ip, size=1000)
                
                confidence = calculate_alt_confidence(user_details, other_user_details)
                
                if confidence >= confidence_threshold:
                    potential_alts.append({
                        'user_id': other_user['user_id'],
                        'shared_ip': ip,
                        'confidence': confidence,
                        'user_activity': summarize_activity(user_details),
                        'alt_activity': summarize_activity(other_user_details)
                    })
    
    return sorted(potential_alts, key=lambda x: x['confidence'], reverse=True)

def summarize_activity(details: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not details:
        return {"error": "No activity data available"}
    
    first_activity = min(detail['_source']['date_first'] for detail in details)
    last_activity = max(detail['_source']['date_last'] for detail in details)
    total_logins = sum(detail['_source']['count'] for detail in details)
    
    return {
        "first_activity": first_activity,
        "last_activity": last_activity,
        "total_logins": total_logins
    }

def calculate_alt_confidence(user_details: List[Dict[str, Any]], other_user_details: List[Dict[str, Any]], weights: Dict[str, float] = None) -> float:
    if not weights:
        weights = {
            'ip_overlap': 0.4,
            'time_proximity': 0.3,
            'activity_pattern': 0.2,
            'login_frequency': 0.1
        }
    
    scores = {
        'ip_overlap': calculate_ip_overlap(user_details, other_user_details),
        'time_proximity': calculate_time_proximity(user_details, other_user_details),
        'activity_pattern': calculate_activity_pattern(user_details, other_user_details),
        'login_frequency': calculate_login_frequency(user_details, other_user_details),
        'user_agent_similarity': calculate_user_agent_similarity(user_details, other_user_details)
    }
    
    # Normalize scores
    for key in scores:
        scores[key] = max(0, min(scores[key], 1))
    
    # Calculate weighted sum
    confidence = sum(scores[key] * weights.get(key, 0) for key in scores)
    
    return confidence

def calculate_ip_overlap(user_details: List[Dict[str, Any]], other_user_details: List[Dict[str, Any]]) -> float:
    try:
        user_ips = set(detail['_source']['ip'] for detail in user_details if detail['_source'].get('ip'))
        other_user_ips = set(detail['_source']['ip'] for detail in other_user_details if detail['_source'].get('ip'))
        if not user_ips or not other_user_ips:
            return 0
        return len(user_ips.intersection(other_user_ips)) / len(user_ips.union(other_user_ips))
    except Exception as e:
        print(f"Error in calculate_ip_overlap: {e}")
        return 0

def calculate_time_proximity(user_details: List[Dict[str, Any]], other_user_details: List[Dict[str, Any]]) -> float:
    try:
        user_timestamps = [parse(detail['_source']['date_last']) for detail in user_details]
        other_user_timestamps = [parse(detail['_source']['date_last']) for detail in other_user_details]
        
        all_timestamps = sorted(user_timestamps + other_user_timestamps)
        time_diffs = [(all_timestamps[i+1] - all_timestamps[i]).total_seconds() for i in range(len(all_timestamps)-1)]
        
        if not time_diffs:
            return 0
        
        avg_time_diff = sum(time_diffs) / len(time_diffs)
        return math.exp(-avg_time_diff / (24 * 3600))  # Exponential decay, 1 day half-life
    except Exception as e:
        print(f"Error in calculate_time_proximity: {e}")
        return 0

def calculate_activity_pattern(user_details: List[Dict[str, Any]], other_user_details: List[Dict[str, Any]]) -> float:
    try:
        user_activity = [detail['_source']['count'] for detail in user_details]
        other_user_activity = [detail['_source']['count'] for detail in other_user_details]
        
        if not user_activity or not other_user_activity:
            return 0
        
        user_mean = statistics.mean(user_activity)
        other_user_mean = statistics.mean(other_user_activity)
        
        if user_mean == 0 and other_user_mean == 0:
            return 1
        elif user_mean == 0 or other_user_mean == 0:
            return 0
        
        return 1 - abs(user_mean - other_user_mean) / max(user_mean, other_user_mean)
    except Exception as e:
        print(f"Error in calculate_activity_pattern: {e}")
        return 0

def calculate_login_frequency(user_details: List[Dict[str, Any]], other_user_details: List[Dict[str, Any]]) -> float:
    try:
        user_frequency = calculate_frequency(user_details)
        other_user_frequency = calculate_frequency(other_user_details)
        
        if user_frequency == 0 and other_user_frequency == 0:
            return 1
        elif user_frequency == 0 or other_user_frequency == 0:
            return 0
        
        return 1 - abs(user_frequency - other_user_frequency) / max(user_frequency, other_user_frequency)
    except Exception as e:
        print(f"Error in calculate_login_frequency: {e}")
        return 0

def calculate_frequency(details: List[Dict[str, Any]]) -> float:
    if not details:
        return 0
    
    try:
        first_activity = min(parse(detail['_source']['date_first']) for detail in details)
        last_activity = max(parse(detail['_source']['date_last']) for detail in details)
        total_logins = sum(detail['_source']['count'] for detail in details)
        
        time_span = (last_activity - first_activity).total_seconds() / 86400
        return total_logins / time_span if time_span > 0 else 0
    except Exception as e:
        print(f"Error in calculate_frequency: {e}")
        return 0

def calculate_user_agent_similarity(user_details: List[Dict[str, Any]], other_user_details: List[Dict[str, Any]]) -> float:
    try:
        user_agents = set(detail['_source'].get('user_agent', '') for detail in user_details)
        other_user_agents = set(detail['_source'].get('user_agent', '') for detail in other_user_details)
        
        if not user_agents or not other_user_agents:
            return 0
        
        return len(user_agents.intersection(other_user_agents)) / len(user_agents.union(other_user_agents))
    except Exception as e:
        print(f"Error in calculate_user_agent_similarity: {e}")
        return 0
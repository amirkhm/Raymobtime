from types import SimpleNamespace
from src.scripts.config import deep_merge, dict_to_namespace

def test_deep_merge_nested_dictionaries():
    default_dict = {
        "pipeline": {
            "mobility": {"enabled": True, "tool": "sumo"},
            "ray_tracing": {"enabled": True, "jump": 1}
        },
        "frequency": 60e9
    }
    user_dict = {
        "pipeline": {
            "mobility": {"tool": "generic"},
            "blensor": {"enabled": False}
        },
        "frequency": 28e9
    }
    
    merged = deep_merge(default_dict, user_dict)
    
    assert merged["pipeline"]["mobility"]["enabled"] is True
    assert merged["pipeline"]["mobility"]["tool"] == "generic"
    assert merged["pipeline"]["ray_tracing"]["enabled"] is True
    assert merged["pipeline"]["blensor"]["enabled"] is False
    assert merged["frequency"] == 28e9

def test_dict_to_namespace_conversion():
    config_dict = {
        "scenario": "rosslyn",
        "limits": [10.5, 20.0],
        "nested": {
            "flag": True
        }
    }
    
    config_ns = dict_to_namespace(config_dict)
    
    assert isinstance(config_ns, SimpleNamespace)
    assert config_ns.scenario == "rosslyn"
    assert config_ns.limits == [10.5, 20.0]
    assert isinstance(config_ns.nested, SimpleNamespace)
    assert config_ns.nested.flag is True

def test_dict_to_namespace_list_of_dicts():
    config_dict = {
        "items": [
            {"id": 1, "val": "A"},
            {"id": 2, "val": "B"}
        ]
    }
    
    config_ns = dict_to_namespace(config_dict)
    
    assert isinstance(config_ns.items, list)
    assert isinstance(config_ns.items[0], SimpleNamespace)
    assert config_ns.items[0].id == 1
    assert config_ns.items[1].val == "B"
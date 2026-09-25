import pytest
from app.scanner.openapi_parser import OpenAPIParser

@pytest.fixture
def sample_openapi_spec():
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Sample API",
            "version": "1.0.0"
        },
        "paths": {
            "/items/{itemId}": {
                "get": {
                    "summary": "Get an item by ID",
                    "parameters": [
                        {
                            "name": "itemId",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {
                                                "type": "string"
                                            },
                                            "name": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

def test_openapi_parser_initialization(sample_openapi_spec):
    parser = OpenAPIParser(sample_openapi_spec)
    assert parser.spec == sample_openapi_spec

def test_get_object_endpoints(sample_openapi_spec):
    parser = OpenAPIParser(sample_openapi_spec)
    endpoints = parser.get_object_endpoints()
    assert len(endpoints) == 1
    assert endpoints[0].path == "/items/{itemId}"

def test_find_paired_collection(sample_openapi_spec):
    parser = OpenAPIParser(sample_openapi_spec)
    endpoint = parser.get_object_endpoints()[0]
    paired = parser.find_paired_collection(endpoint)
    assert paired is None  # Assuming no paired collection exists in this sample spec

def test_invalid_spec_initialization():
    with pytest.raises(ValueError):
        OpenAPIParser(None)  # Should raise an error for invalid spec

def test_empty_paths(sample_openapi_spec):
    empty_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Empty API",
            "version": "1.0.0"
        },
        "paths": {}
    }
    parser = OpenAPIParser(empty_spec)
    endpoints = parser.get_object_endpoints()
    assert endpoints == []  # No endpoints should be found in an empty spec
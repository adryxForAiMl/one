from app.scanner.openapi_parser import OpenAPIParser

def test_openapi_parser_valid_spec():
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Sample API",
            "version": "1.0.0"
        },
        "paths": {
            "/items": {
                "get": {
                    "summary": "Get items",
                    "responses": {
                        "200": {
                            "description": "A list of items"
                        }
                    }
                }
            }
        }
    }
    parser = OpenAPIParser(spec)
    assert parser.get_object_endpoints() == [
        {
            "path": "/items",
            "parameter": None,
            "collection_path": "/items"
        }
    ]

def test_openapi_parser_invalid_spec():
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Sample API",
            "version": "1.0.0"
        },
        "paths": {}
    }
    parser = OpenAPIParser(spec)
    assert parser.get_object_endpoints() == []

def test_openapi_parser_with_parameters():
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Sample API",
            "version": "1.0.0"
        },
        "paths": {
            "/items/{itemId}": {
                "get": {
                    "summary": "Get an item",
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
                            "description": "An item"
                        }
                    }
                }
            }
        }
    }
    parser = OpenAPIParser(spec)
    assert parser.get_object_endpoints() == [
        {
            "path": "/items/{itemId}",
            "parameter": "itemId",
            "collection_path": "/items"
        }
    ]
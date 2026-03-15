// knowledge/api-contracts/swagger-parser.ts
// Utilidad para parsear especificaciones OpenAPI/Swagger

export interface OpenApiSpec {
    openapi: string;
    info: {
        title: string;
        version: string;
        description?: string;
    };
    servers: Array<{ url: string; description?: string }>;
    paths: Record<string, PathItem>;
    components: {
        schemas: Record<string, Schema>;
    };
}

export interface PathItem {
    get?: Operation;
    post?: Operation;
    put?: Operation;
    delete?: Operation;
    patch?: Operation;
}

export interface Operation {
    operationId: string;
    summary?: string;
    description?: string;
    tags?: string[];
    parameters?: Parameter[];
    requestBody?: RequestBody;
    responses: Record<string, Response>;
}

export interface Parameter {
    name: string;
    in: 'query' | 'header' | 'path' | 'cookie';
    required?: boolean;
    schema: Schema;
}

export interface RequestBody {
    required?: boolean;
    content: {
        'application/json': {
            schema: Schema;
        };
    };
}

export interface Response {
    description: string;
    content?: {
        'application/json': {
            schema: Schema;
        };
    };
}

export interface Schema {
    type: 'string' | 'number' | 'integer' | 'boolean' | 'array' | 'object';
    format?: string;
    properties?: Record<string, Schema>;
    items?: Schema;
    required?: string[];
    enum?: any[];
    $ref?: string;
}

/**
 * Parsea una especificación OpenAPI y extrae información útil para generar código Angular
 */
export function parseOpenApiSpec(spec: OpenApiSpec): ParsedSpec {
    const endpoints: Endpoint[] = [];
    const interfaces: TypeScriptInterface[] = [];

    // Extraer endpoints
    for (const [path, pathItem] of Object.entries(spec.paths)) {
        for (const [method, operation] of Object.entries(pathItem)) {
            if (['get', 'post', 'put', 'delete', 'patch'].includes(method)) {
                endpoints.push({
                    path,
                    method: method.toUpperCase(),
                    operationId: operation.operationId,
                    summary: operation.summary,
                    tags: operation.tags || [],
                    parameters: operation.parameters || [],
                    requestBody: operation.requestBody,
                    responses: operation.responses
                });
            }
        }
    }

    // Extraer esquemas como interfaces TypeScript
    for (const [name, schema] of Object.entries(spec.components.schemas)) {
        interfaces.push({
            name,
            properties: schema.properties || {},
            required: schema.required || []
        });
    }

    return {
        info: spec.info,
        baseUrl: spec.servers[0]?.url || '',
        endpoints,
        interfaces
    };
}

export interface ParsedSpec {
    info: OpenApiSpec['info'];
    baseUrl: string;
    endpoints: Endpoint[];
    interfaces: TypeScriptInterface[];
}

export interface Endpoint {
    path: string;
    method: string;
    operationId: string;
    summary?: string;
    tags: string[];
    parameters: Parameter[];
    requestBody?: RequestBody;
    responses: Record<string, Response>;
}

export interface TypeScriptInterface {
    name: string;
    properties: Record<string, Schema>;
    required: string[];
}
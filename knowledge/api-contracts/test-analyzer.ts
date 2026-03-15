// knowledge/api-contracts/test-analyzer.ts
// Utilidad para analizar tests de backend e inferir contratos de API

export interface TestAnalysis {
    endpoints: InferredEndpoint[];
    requestTypes: InferredType[];
    responseTypes: InferredType[];
    errorCases: ErrorCase[];
}

export interface InferredEndpoint {
    method: string;
    path: string;
    description: string;
    requestType?: string;
    responseType?: string;
    errorCodes: number[];
}

export interface InferredType {
    name: string;
    properties: Array<{ name: string; type: string; required: boolean }>;
}

export interface ErrorCase {
    statusCode: number;
    description: string;
    example: string;
}

/**
 * Analiza tests de backend (Jest/JUnit) para inferir contratos de API
 */
export function analyzeBackendTests(testContent: string): TestAnalysis {
    const analysis: TestAnalysis = {
        endpoints: [],
        requestTypes: [],
        responseTypes: [],
        errorCases: []
    };

    // Extraer endpoints de describe/it blocks
    const endpointRegex = /(?:describe|it)\(['"](?:GET|POST|PUT|DELETE|PATCH)\s+([^'"]+)['"]/g;
    let match;
    while ((match = endpointRegex.exec(testContent)) !== null) {
        const [fullMatch, pathWithMethod] = match;
        const [method, path] = pathWithMethod.split(' ');

        analysis.endpoints.push({
            method,
            path,
            description: extractDescription(testContent, fullMatch),
            errorCodes: extractErrorCodes(testContent, fullMatch)
        });
    }

    // Extraer tipos de request/response de mocks
    const mockRegex = /mock(?:Request|Response)\(\{([^}]+)\}\)/g;
    while ((match = mockRegex.exec(testContent)) !== null) {
        const properties = extractProperties(match[1]);
        analysis.requestTypes.push({
            name: 'InferredRequest',
            properties
        });
    }

    // Extraer casos de error
    const errorRegex = /expect.*status.*toBe\((\d+)\)/g;
    while ((match = errorRegex.exec(testContent)) !== null) {
        const statusCode = parseInt(match[1]);
        analysis.errorCases.push({
            statusCode,
            description: getErrorDescription(statusCode),
            example: match[0]
        });
    }

    return analysis;
}

function extractDescription(content: string, marker: string): string {
    const lines = content.split('\n');
    const markerIndex = lines.findIndex(l => l.includes(marker));
    if (markerIndex > 0) {
        const descLine = lines[markerIndex - 1];
        const descMatch = descLine.match(/\/\/\s*(.+)/);
        if (descMatch) return descMatch[1].trim();
    }
    return 'Endpoint inferido desde tests';
}

function extractErrorCodes(content: string, marker: string): number[] {
    const codes: number[] = [];
    const errorMatches = content.matchAll(/status.*toBe\((\d+)\)/g);
    for (const match of errorMatches) {
        codes.push(parseInt(match[1]));
    }
    return [...new Set(codes)];
}

function extractProperties(objString: string): Array<{ name: string; type: string; required: boolean }> {
    const properties: Array<{ name: string; type: string; required: boolean }> = [];
    const propRegex = /(\w+):\s*(?:"[^"]*"|'[^']*'|\d+|true|false|\[\])/g;
    let match;
    while ((match = propRegex.exec(objString)) !== null) {
        const value = match[2];
        properties.push({
            name: match[1],
            type: inferType(value),
            required: true
        });
    }
    return properties;
}

function inferType(value: string): string {
    if (value.startsWith('"') || value.startsWith("'")) return 'string';
    if (value === 'true' || value === 'false') return 'boolean';
    if (!isNaN(Number(value))) return 'number';
    if (value.startsWith('[')) return 'array';
    return 'any';
}

function getErrorDescription(code: number): string {
    const descriptions: Record<number, string> = {
        400: 'Bad Request - Datos inválidos',
        401: 'Unauthorized - No autenticado',
        403: 'Forbidden - Sin permisos',
        404: 'Not Found - Recurso no existe',
        500: 'Internal Server Error'
    };
    return descriptions[code] || `Error ${code}`;
}
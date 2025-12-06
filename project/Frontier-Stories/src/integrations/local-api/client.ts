// Local API Client for Frontier-Stories
// Supabase-compatible interface for local development

const API_BASE_URL = import.meta.env.VITE_SUPABASE_URL || 'http://localhost:3001';

interface ApiResponse<T> {
  data: T | null;
  error: string | null;
}

// Query builder to match Supabase interface
class QueryBuilder<T> {
  private endpoint: string;
  private method: string = 'GET';
  private body: any = null;

  constructor(endpoint: string) {
    this.endpoint = endpoint;
  }

  select(columns: string = '*'): QueryBuilder<T> {
    // For now, ignore column selection - return all
    return this;
  }

  eq(column: string, value: any): QueryBuilder<T> {
    // Simple filtering - append to endpoint
    const separator = this.endpoint.includes('?') ? '&' : '?';
    this.endpoint += `${separator}${column}=${encodeURIComponent(value)}`;
    return this;
  }

  insert(data: any): QueryBuilder<T> {
    this.method = 'POST';
    this.body = data;
    return this;
  }

  update(data: any): QueryBuilder<T> {
    this.method = 'PUT';
    this.body = data;
    return this;
  }

  delete(): QueryBuilder<T> {
    this.method = 'DELETE';
    return this;
  }

  // Make QueryBuilder thenable to match Supabase interface
  then<TResult1 = ApiResponse<T[]>, TResult2 = never>(
    onfulfilled?: ((value: ApiResponse<T[]>) => TResult1 | PromiseLike<TResult1>) | null,
    onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | null
  ): Promise<TResult1 | TResult2> {
    return this.execute().then(onfulfilled, onrejected);
  }

  catch<TResult = never>(
    onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | null
  ): Promise<ApiResponse<T[]> | TResult> {
    return this.execute().catch(onrejected);
  }

  finally(onfinally?: (() => void) | null): Promise<ApiResponse<T[]>> {
    return this.execute().finally(onfinally);
  }

  async execute(): Promise<ApiResponse<T[]>> {
    try {
      const response = await fetch(`${API_BASE_URL}${this.endpoint}`, {
        method: this.method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: this.body ? JSON.stringify(this.body) : null,
      });

      const result = await response.json();
      
      if (!response.ok) {
        return { data: null, error: result.error || `HTTP ${response.status}` };
      }
      
      // Handle single object vs array responses
      const data = Array.isArray(result.data) ? result.data : [result.data];
      return { data, error: null };
    } catch (error) {
      console.error('API request failed:', error);
      return { data: null, error: error.message };
    }
  }
}

class LocalApiClient {
  from(table: string): QueryBuilder<any> {
    return new QueryBuilder(`/${table}`);
  }

  // Direct methods for simple operations
  async rpc(functionName: string, params: any = {}) {
    const response = await fetch(`${API_BASE_URL}/rpc/${functionName}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });
    
    return response.json();
  }

  // Storage methods (placeholder)
  storage = {
    from: (bucket: string) => ({
      upload: (path: string, file: File) => {
        console.log('Storage upload not implemented in local mode');
        return Promise.resolve({ data: null, error: 'Storage not available locally' });
      },
      getPublicUrl: (path: string) => ({
        data: { publicUrl: `http://localhost:3001/storage/${bucket}/${path}` }
      }),
    }),
  };

  // Auth methods (placeholder)
  auth = {
    getUser: () => Promise.resolve({ data: { user: null }, error: null }),
    signIn: () => Promise.resolve({ data: null, error: 'Auth not available locally' }),
    signOut: () => Promise.resolve({ data: null, error: null }),
  };
}

export const supabase = new LocalApiClient();

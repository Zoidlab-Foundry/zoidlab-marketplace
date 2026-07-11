export interface Agent {
  id: string;
  name: string;
  slug: string;
  short_description: string;
  long_description?: string;
  category: string;
  tags: string[];
  icon: string;
  accent: string;
  publisher_name: string;
  publisher_user_id?: string | null;
  visibility: "public" | "verified" | "private" | "organization";
  status: string;
  version: string;
  manifest?: any;
  required_models: any[];
  required_tools: any[];
  required_secrets: any[];
  permissions: { name: string; description: string }[];
  input_schema?: any;
  output_schema?: any;
  risk: "low" | "medium" | "high";
  featured: boolean;
  install_count: number;
  rating_avg: number;
  rating_count: number;
  created_at?: string;
  updated_at?: string;
  badges?: string[];
  versions?: { id: string; version: string; changelog: string; created_at: string }[];
  installed?: boolean;
  // present on My Agents rows
  install_id?: string;
  install_status?: string;
  installed_at?: string;
  installed_config?: any;
}

export interface Category { name: string; count: number; }

export interface TestResult {
  output: { response: string; intent: string; confidence: number };
  latency_ms: number;
  cost_estimate: number;
  logs: { step: string; detail: string }[];
}

export interface WhoAmI {
  authenticated: boolean;
  email?: string;
  name?: string;
  tier?: string;
  admin?: boolean;
}

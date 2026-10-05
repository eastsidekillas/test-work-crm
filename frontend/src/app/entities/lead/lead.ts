import { Tag } from "../tag/tag";
export interface Lead {
  id: number;
  name: string;
  contact: string;
  request: string;
  source: "manual" | "telegram_bot";
  created_at: string;
  tags: Tag[];
}
export interface NewLead {
  name: string;
  contact: string;
  request: string;
}
export interface LeadPage {
  count: number;
  next: string | null;
  previous: string | null;
  results: Lead[];
}

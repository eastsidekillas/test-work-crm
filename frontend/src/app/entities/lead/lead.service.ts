import { Injectable, inject } from "@angular/core";
import { ApiService } from "../../shared/api/api.service";
import { Lead, LeadPage, NewLead } from "./lead";
@Injectable({ providedIn: "root" })
export class LeadService {
  private api = inject(ApiService);
  list(page = 1, tagId: number | null = null) {
    return this.api.request<LeadPage>(
      `leads/?page=${page}${tagId ? "&tag_id=" + tagId : ""}`,
    );
  }
  create(lead: NewLead) {
    return this.api.request<Lead>("leads/", "POST", lead);
  }
  setTags(id: number, tagIds: number[]) {
    return this.api.request<Lead>(`leads/${id}/`, "PATCH", { tag_ids: tagIds });
  }
}

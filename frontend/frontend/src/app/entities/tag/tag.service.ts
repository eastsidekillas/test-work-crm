import { Injectable, inject } from '@angular/core';
import { ApiService } from '../../shared/api/api.service';
import { Tag } from './tag';
@Injectable({ providedIn: 'root' })
export class TagService {
  private api = inject(ApiService);
  list() { return this.api.request<Tag[]>('tags/'); }
  create(name: string) { return this.api.request<Tag>('tags/', 'POST', { name }); }
}

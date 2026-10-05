import { Component, OnInit, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../entities/user/auth.service';
import { Lead, LeadPage } from '../../entities/lead/lead';
import { LeadService } from '../../entities/lead/lead.service';
import { Tag } from '../../entities/tag/tag';
import { TagService } from '../../entities/tag/tag.service';
import { CreateLeadComponent } from '../../features/create-lead/create-lead.component';
import { CreateTagComponent } from '../../features/create-tag/create-tag.component';
import { AssignTagsComponent } from '../../features/assign-tags/assign-tags.component';
import { ApiError, messageOf } from '../../shared/api/api.service';
@Component({ selector: 'crm-leads-page', imports: [DatePipe, CreateLeadComponent, CreateTagComponent, AssignTagsComponent], templateUrl: './leads.component.html' })
export class LeadsComponent implements OnInit {
  auth = inject(AuthService); private leadsApi = inject(LeadService); private tagsApi = inject(TagService); private router = inject(Router);
  data = signal<LeadPage>({ count: 0, next: null, previous: null, results: [] }); tags = signal<Tag[]>([]);
  loading = signal(true); error = signal(''); notice = signal(''); filter = signal<number | null>(null); page = signal(1);
  createLead = signal(false); createTag = signal(false); editing = signal<Lead | null>(null); loggingOut = signal(false);
  private loadSequence = 0;
  ngOnInit() { void this.load(); }
  async load() {
    const sequence = ++this.loadSequence; this.loading.set(true); this.error.set('');
    try {
      const [data, tags] = await Promise.all([this.leadsApi.list(this.page(), this.filter()), this.tagsApi.list()]);
      if (sequence === this.loadSequence) { this.data.set(data); this.tags.set(tags); }
    } catch (error) { if (sequence === this.loadSequence) { if (error instanceof ApiError && error.status === 403) this.expired(); else this.error.set(messageOf(error)); } }
    finally { if (sequence === this.loadSequence) this.loading.set(false); }
  }
  selectTag(id: number | null) { this.filter.set(id); this.page.set(1); this.notice.set(''); void this.load(); }
  changePage(delta: number) { this.page.update(p => Math.max(1, p + delta)); void this.load(); }
  async addedLead() { this.createLead.set(false); this.filter.set(null); this.page.set(1); this.notice.set('Лид добавлен.'); await this.load(); }
  async addedTag() { this.createTag.set(false); this.notice.set('Тег создан.'); await this.load(); }
  async assignedTags() { this.editing.set(null); this.page.set(1); this.notice.set('Теги сохранены.'); await this.load(); }
  expired() { this.auth.user.set(null); void this.router.navigateByUrl('/login'); }
  async logout() {
    if (this.loggingOut()) return; this.loggingOut.set(true);
    try { await this.auth.logout(); this.expired(); }
    catch (error) { if (error instanceof ApiError && error.status === 403) this.expired(); else this.error.set(messageOf(error)); }
    finally { this.loggingOut.set(false); }
  }
}

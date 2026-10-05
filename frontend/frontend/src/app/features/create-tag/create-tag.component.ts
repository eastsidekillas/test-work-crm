import { Component, inject, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TagService } from '../../entities/tag/tag.service';
import { ModalComponent } from '../../shared/ui/modal.component';
import { ApiError, messageOf } from '../../shared/api/api.service';
@Component({ selector: 'crm-create-tag', imports: [FormsModule, ModalComponent], template: `
<crm-modal title="Новый тег" [busy]="busy()" (dismissed)="closed.emit()">
<form (ngSubmit)="submit()" class="space-y-5">
<label class="field-label">Название тега<input name="name" [(ngModel)]="name" required maxlength="50" placeholder="Например, Разработка сайта" [disabled]="busy()"></label>
@if (error()) { <p class="error" role="alert">{{ error() }}</p> }
<div class="modal-actions"><button type="button" class="button" [disabled]="busy()" (click)="closed.emit()">Отмена</button><button class="button primary" [disabled]="busy() || !name.trim()">{{ busy() ? 'Сохраняем…' : 'Сохранить тег' }}</button></div>
</form></crm-modal>` })
export class CreateTagComponent {
  private tags = inject(TagService); saved = output<void>(); closed = output<void>(); expired = output<void>();
  name = ''; busy = signal(false); error = signal('');
  async submit() {
    if (this.busy()) return; this.busy.set(true); this.error.set('');
    try { await this.tags.create(this.name.trim()); this.saved.emit(); }
    catch (error) { if (error instanceof ApiError && error.status === 403) this.expired.emit(); else this.error.set(messageOf(error)); }
    finally { this.busy.set(false); }
  }
}

import {
  Component,
  OnInit,
  inject,
  input,
  output,
  signal,
} from "@angular/core";
import { Lead } from "../../entities/lead/lead";
import { LeadService } from "../../entities/lead/lead.service";
import { Tag } from "../../entities/tag/tag";
import { ModalComponent } from "../../shared/ui/modal.component";
import { ApiError, messageOf } from "../../shared/api/api.service";
@Component({
  selector: "crm-assign-tags",
  imports: [ModalComponent],
  template: ` <crm-modal
    title="Теги заявки"
    [busy]="busy()"
    (dismissed)="closed.emit()"
  >
    <p class="text-sm muted mb-5">{{ lead().name }}</p>
    @if (tags().length) {
      <div class="space-y-3 mb-6">
        @for (tag of tags(); track tag.id) {
          <label class="check-label"
            ><input
              type="checkbox"
              [checked]="selected.has(tag.id)"
              [disabled]="busy()"
              (change)="toggle(tag.id)"
            />{{ tag.name }}</label
          >
        }
      </div>
    } @else {
      <p class="muted mb-6">Сначала создайте тег на странице заявок.</p>
    }
    @if (error()) {
      <p class="error mb-4" role="alert">{{ error() }}</p>
    }
    <div class="modal-actions">
      <button class="button" [disabled]="busy()" (click)="closed.emit()">
        Отмена</button
      ><button class="button primary" [disabled]="busy()" (click)="save()">
        {{ busy() ? "Сохраняем…" : "Сохранить теги" }}
      </button>
    </div>
  </crm-modal>`,
})
export class AssignTagsComponent implements OnInit {
  private leads = inject(LeadService);
  lead = input.required<Lead>();
  tags = input.required<Tag[]>();
  saved = output<void>();
  closed = output<void>();
  expired = output<void>();
  selected = new Set<number>();
  busy = signal(false);
  error = signal("");
  ngOnInit() {
    this.selected = new Set(this.lead().tags.map((t) => t.id));
  }
  toggle(id: number) {
    if (this.selected.has(id)) this.selected.delete(id);
    else this.selected.add(id);
  }
  async save() {
    if (this.busy()) return;
    this.busy.set(true);
    this.error.set("");
    try {
      await this.leads.setTags(this.lead().id, [...this.selected]);
      this.saved.emit();
    } catch (error) {
      if (error instanceof ApiError && error.status === 403)
        this.expired.emit();
      else this.error.set(messageOf(error));
    } finally {
      this.busy.set(false);
    }
  }
}

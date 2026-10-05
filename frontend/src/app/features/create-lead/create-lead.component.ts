import { Component, inject, output, signal } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { LeadService } from "../../entities/lead/lead.service";
import { ModalComponent } from "../../shared/ui/modal.component";
import { ApiError, messageOf } from "../../shared/api/api.service";
@Component({
  selector: "crm-create-lead",
  imports: [FormsModule, ModalComponent],
  template: ` <crm-modal
    title="Новая заявка"
    [busy]="busy()"
    (dismissed)="closed.emit()"
  >
    <form (ngSubmit)="submit()" #form="ngForm" class="space-y-5">
      <label class="field-label"
        >Имя<input
          name="name"
          [(ngModel)]="name"
          required
          maxlength="150"
          autocomplete="name"
          [disabled]="busy()"
      /></label>
      <label class="field-label"
        >Контакт<input
          name="contact"
          [(ngModel)]="contact"
          required
          maxlength="255"
          placeholder="Телефон, email или @username"
          [disabled]="busy()"
      /></label>
      <label class="field-label"
        >Запрос<textarea
          name="request"
          [(ngModel)]="request"
          required
          maxlength="5000"
          rows="4"
          placeholder="С чем нужна помощь?"
          [disabled]="busy()"
        ></textarea>
      </label>
      @if (error()) {
        <p class="error" role="alert">{{ error() }}</p>
      }
      <div class="modal-actions">
        <button
          type="button"
          class="button"
          [disabled]="busy()"
          (click)="closed.emit()"
        >
          Отмена</button
        ><button
          class="button primary"
          [disabled]="
            busy() ||
            form.invalid ||
            !name.trim() ||
            !contact.trim() ||
            !request.trim()
          "
        >
          {{ busy() ? "Сохраняем…" : "Сохранить лид" }}
        </button>
      </div>
    </form></crm-modal
  >`,
})
export class CreateLeadComponent {
  private leads = inject(LeadService);
  saved = output<void>();
  closed = output<void>();
  expired = output<void>();
  name = "";
  contact = "";
  request = "";
  busy = signal(false);
  error = signal("");
  async submit() {
    if (this.busy()) return;
    this.busy.set(true);
    this.error.set("");
    try {
      await this.leads.create({
        name: this.name.trim(),
        contact: this.contact.trim(),
        request: this.request.trim(),
      });
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

import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild,
  input,
  output,
} from "@angular/core";
@Component({
  selector: "crm-modal",
  template: ` <dialog
    #dialog
    (cancel)="cancel($event)"
    aria-labelledby="modal-title"
  >
    <header class="flex items-center justify-between gap-4 mb-6">
      <h2 id="modal-title" class="text-xl font-semibold">{{ title() }}</h2>
      <button
        type="button"
        class="icon-button"
        aria-label="Закрыть"
        [disabled]="busy()"
        (click)="dismissed.emit()"
      >
        ✕
      </button>
    </header>
    <ng-content />
  </dialog>`,
})
export class ModalComponent implements AfterViewInit, OnDestroy {
  title = input.required<string>();
  busy = input(false);
  dismissed = output<void>();
  @ViewChild("dialog") dialog!: ElementRef<HTMLDialogElement>;
  ngAfterViewInit() {
    this.dialog.nativeElement.showModal();
  }
  ngOnDestroy() {
    this.dialog.nativeElement.close();
  }
  cancel(event: Event) {
    event.preventDefault();
    if (!this.busy()) this.dismissed.emit();
  }
}

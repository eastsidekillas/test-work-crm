import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../entities/user/auth.service';
import { messageOf } from '../../shared/api/api.service';
@Component({ selector: 'crm-sign-in', imports: [FormsModule], template: `
<form (ngSubmit)="submit()" class="space-y-5">
  <label class="field-label">Логин<input name="username" [(ngModel)]="username" autocomplete="username" required maxlength="150" [disabled]="busy()"></label>
  <label class="field-label">Пароль<input name="password" [(ngModel)]="password" type="password" autocomplete="current-password" required maxlength="256" [disabled]="busy()"></label>
  @if (error()) { <p class="error" role="alert">{{ error() }}</p> }
  <button class="button primary w-full" [disabled]="busy() || !username.trim() || !password">{{ busy() ? 'Входим…' : 'Войти' }}</button>
</form>` })
export class SignInComponent {
  private auth = inject(AuthService); private router = inject(Router);
  username = ''; password = ''; busy = signal(false); error = signal('');
  async submit() {
    if (this.busy()) return; this.busy.set(true); this.error.set('');
    try { await this.auth.login(this.username.trim(), this.password); await this.router.navigateByUrl('/leads'); }
    catch (error) { this.error.set(messageOf(error)); } finally { this.busy.set(false); }
  }
}

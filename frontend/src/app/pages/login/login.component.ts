import { Component } from "@angular/core";
import { SignInComponent } from "../../features/sign-in/sign-in.component";
@Component({
  selector: "crm-login-page",
  imports: [SignInComponent],
  template: ` <main class="min-h-dvh px-4 py-16">
    <section class="mx-auto max-w-sm border border-gray-300 bg-white p-6">
      <h1 class="mb-6 text-xl font-semibold">Вход в CRM</h1>
      <crm-sign-in />
    </section>
  </main>`,
})
export class LoginComponent {}

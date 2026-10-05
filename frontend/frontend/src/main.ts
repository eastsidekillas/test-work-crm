import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { RootComponent } from './app/app/root.component';
import { routes } from './app/app/routes';
bootstrapApplication(RootComponent, { providers: [provideRouter(routes)] }).catch(console.error);

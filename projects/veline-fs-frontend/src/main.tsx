import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/App.css";
import ErrorBoundary from "./components/ErrorBoundary";
import { NextUIProvider } from "@nextui-org/react";
ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <ErrorBoundary>
      <NextUIProvider>
        <App />
      </NextUIProvider>
    </ErrorBoundary>
  </React.StrictMode>
);

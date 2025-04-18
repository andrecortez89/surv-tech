import React from "react";
import FormularioAuditoria from "./components/FormularioAuditoria";
import DashboardAuditoria from "./components/DashboardAuditoria";

export default function App() {
  return (
    <div className="p-6 font-sans">
      <h1 className="text-2xl font-bold mb-4">Auditoria de Higiene das Mãos</h1>
      <FormularioAuditoria />
      <hr className="my-6" />
      <DashboardAuditoria />
    </div>
  );
}

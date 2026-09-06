import React from 'react';
import { Navigate } from 'react-router-dom';

import ControlTowerScreen from './screens/ControlTowerScreen';
import SignalsScreen from './screens/SignalsScreen';
import SignalDetailScreen from './screens/SignalDetailScreen';
import ApprovalsScreen from './screens/approvals/ApprovalsScreen';
import ApprovalDetailScreen from './screens/approvals/ApprovalDetailScreen';
import InventoryScreen from './screens/InventoryScreen';
import ProductDetailScreen from './screens/ProductDetailScreen';
import SuppliersScreen from './screens/SuppliersScreen';
import SupplierScorecardScreen from './screens/SupplierScorecardScreen';
import ReceivingScreen from './screens/ReceivingScreen';
import ReceiptEntryScreen from './screens/ReceiptEntryScreen';
import DecisionsScreen from './screens/decisions/DecisionsScreen';
import DecisionDetailScreen from './screens/decisions/DecisionDetailScreen';
import ImpactScreen from './screens/ImpactScreen';
import AutonomySettingsScreen from './screens/AutonomySettingsScreen';
import ScenariosSettingsScreen from './screens/ScenariosSettingsScreen';

/**
 * STEWARD Routing Table
 * Exact 17 addressable routes unblocking all operational and governance surfaces.
 */
export const routes = [
  {
    path: '/',
    element: <Navigate to="/tower" replace />,
  },
  {
    path: '/tower',
    element: <ControlTowerScreen />,
  },
  {
    path: '/signals',
    element: <SignalsScreen />,
  },
  {
    path: '/signals/:signalId',
    element: <SignalDetailScreen />,
  },
  {
    path: '/approvals',
    element: <ApprovalsScreen />,
  },
  {
    path: '/approvals/:approvalId',
    element: <ApprovalDetailScreen />,
  },
  {
    path: '/inventory',
    element: <InventoryScreen />,
  },
  {
    path: '/inventory/:sku',
    element: <ProductDetailScreen />,
  },
  {
    path: '/suppliers',
    element: <SuppliersScreen />,
  },
  {
    path: '/suppliers/:supplierId',
    element: <SupplierScorecardScreen />,
  },
  {
    path: '/receiving',
    element: <ReceivingScreen />,
  },
  {
    path: '/receiving/:poNumber',
    element: <ReceiptEntryScreen />,
  },
  {
    path: '/decisions',
    element: <DecisionsScreen />,
  },
  {
    path: '/decisions/:decisionId',
    element: <DecisionDetailScreen />,
  },
  {
    path: '/impact',
    element: <ImpactScreen />,
  },
  {
    path: '/settings/autonomy',
    element: <AutonomySettingsScreen />,
  },
  {
    path: '/settings/scenarios',
    element: <ScenariosSettingsScreen />,
  },
  {
    path: '*',
    element: <Navigate to="/tower" replace />,
  },
];

export default routes;

import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30, // 30 seconds
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => {
        // Do not retry 401 or 403 or 422 refusal
        if (error?.response?.status === 401 || error?.response?.status === 403 || error?.response?.status === 422) {
          return false;
        }
        return failureCount < 2;
      },
    },
  },
});

/**
 * 15-SHARED-CONTRACTS.md §13.2 Frozen Query Keys
 */
export const QUERY_KEYS = {
  signals: (filters) => filters ? ['signals', filters] : ['signals'],
  signal: (signalId) => ['signal', signalId],
  decisions: (filters) => filters ? ['decisions', filters] : ['decisions'],
  decision: (decisionId) => ['decision', decisionId],
  approvalsPending: () => ['approvals', 'pending'],
  approval: (approvalId) => ['approval', approvalId],
  policies: () => ['policies'],
  impact: () => ['impact'],
  impactGaps: () => ['impact', 'gaps'],
  supplierScorecard: (supplierId) => ['supplier', supplierId, 'scorecard'],
  tower: () => ['tower'],
  products: () => ['products'],
  product: (productId) => ['product', productId],
  suppliers: () => ['suppliers'],
  orders: () => ['orders'],
  dashboard: () => ['dashboard'],
};

/**
 * Invalidation helper following 15 §13.2:
 * "After an approval mutation, invalidate ['approvals','pending'], ['decisions'], and ['tower']."
 */
export function invalidateAfterApproval(client = queryClient) {
  client.invalidateQueries({ queryKey: ['approvals', 'pending'] });
  client.invalidateQueries({ queryKey: ['decisions'] });
  client.invalidateQueries({ queryKey: ['tower'] });
}

import React from 'react';

const VerifierBadge = ({ confidence }) => {
  const badgeConfig = {
    high: {
      Icon: () => <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />,
      color: 'text-green-500',
      label: 'Verified',
    },
    medium: {
      Icon: () => <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />,
      color: 'text-yellow-500',
      label: 'Partial',
    },
    low: {
      Icon: () => <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />,
      color: 'text-red-500',
      label: 'Unverified',
    },
    refusal: {
       Icon: () => <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />,
      color: 'text-gray-500',
      label: 'Refusal',
    },
  };

  const current = badgeConfig[confidence] || badgeConfig.low;

  return (
    <div className={`flex items-center justify-center w-8 h-8 rounded-full bg-white shadow-sm border border-gray-200`} title={current.label}>
      <svg className={`w-5 h-5 ${current.color}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <current.Icon />
      </svg>
    </div>
  );
};

export default VerifierBadge;

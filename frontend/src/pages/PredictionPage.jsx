import React from 'react';
import PredictionView from '../components/PredictionView';

export default function PredictionPage({ filterOptions }) {
  return (
    <div>
      <PredictionView filterOptions={filterOptions} />
    </div>
  );
}

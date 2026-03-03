import React from 'react';
import TransportMap from './components/TransportMap';
import TransportList from './components/TransportList';

function App() {
  return (
    <div>
      <h1>PTV Tracker</h1>
      <TransportMap />
      <TransportList />
    </div>
  );
}

export default App;

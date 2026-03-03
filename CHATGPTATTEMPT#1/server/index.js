const express = require('express');
const app = express();
const PORT = process.env.PORT || 5000;

// Example endpoint for transport data
app.get('/api/transport', (req, res) => {
  res.json({
    trains: [{ name: 'Southern Cross', time: '10:15am' }],
    trams: [{ route: '96', time: '10:20am' }],
    buses: [{ route: '200', time: '10:30am' }],
  });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

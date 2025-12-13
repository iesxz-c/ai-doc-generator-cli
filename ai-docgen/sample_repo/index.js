const http = require('node:http'); // Import the built-in HTTP module
const hostname = '127.0.0.1'; // The server's address (localhost)
const port = 3000; // The port to listen on

// Create a server object
const server = http.createServer((req, res) => {
  // Set the response status code and headers
  res.statusCode = 200;
  res.setHeader('Content-Type', 'text/plain');
  // Send the response body
  res.end('Hello, World!\n');
});

// Start the server and listen on the specified port and hostname
server.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});

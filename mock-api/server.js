var fs         = require('fs');
var jsonServer = require('json-server')

routes = JSON.parse(fs.readFileSync('routes.json'))

var server = jsonServer.create()
server.use(jsonServer.defaults())
server.use(jsonServer.rewriter(routes))
server.use(function (request, response, next) {
  // Respond all POST requests with 200 ignoring the request
  if (request.method === 'POST') {
    response.jsonp(request.query)
  }
  else {
    next()
  }
})
server.use(jsonServer.router(__dirname + '/api.json'))
server.listen(4000, function () {
  console.log('Mock API server is running')
})

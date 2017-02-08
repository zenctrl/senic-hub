var jsonServer = require('json-server')

var server = jsonServer.create()
server.use(jsonServer.defaults())
server.use(jsonServer.rewriter({
  "/-/": "/",
  "/setup/wifi": "/setup-wifi"
}))
server.use(function (req, res, next) {
  // Respond all POST requests with 200 ignoring the request
  if (req.method === 'POST') {
    res.jsonp(req.query)
  }
  else {
    next()
  }
})
server.use(jsonServer.router(__dirname + '/api.json'))
server.listen(4000, function () {
  console.log('Mock API server is running')
})

'use strict'
// Template version: 1.3.1
// see http://vuejs-templates.github.io/webpack for documentation.

const path = require('path')

module.exports = {
  dev: {

    // Paths
    assetsSubDirectory: 'static',
    assetsPublicPath: '/',
    proxyTable: {


      "/eniro/*": {
        target: "http://localhost:8001/eniro",
        secure: false
      },
      "/uploaded/*": {
        target: "http://localhost:8001/uploaded",
        secure: false
      },

      //NEW
      //Route our front end file upload POST to FastAPI’s /upload log endpoint
      "/upload-log": {
        target: "http://localhost:8001",
        changeOrigin: true,    //ensure host header matches backend
      },

      //route all other API calls (like chat) under /api/* to FastAPI
      "/api": {
        target: "http://localhost:8001",
        changeOrigin: true,    //same origin for cookies, CORS, etc.
        //secure: false          //allow self-signed / dev certs if needed
      },

      //Route ping endpoint for testing
      "/ping": {
        target: "http://localhost:8001",
        changeOrigin: true,
      },
    },

    //Various Dev Server settings
    host: '0.0.0.0', //can be overwritten by process.env.HOST
    port: 8080,        //can be overwritten by process.env.PORT
    autoOpenBrowser: false,
    errorOverlay: true,
    notifyOnErrors: true,
    poll: false,       //https://webpack.js.org/configuration/dev-server/#devserver-watchoptions-

    //Use Eslint Loader?
    useEslint: true,
    showEslintErrorsInOverlay: false,
    stats: {
      "errors": true,
      "warnings": true
    },
    /**
     * Source Maps
     */
    devtool: 'eval',   // https://webpack.js.org/configuration/devtool/#development
    cacheBusting: true,
    cssSourceMap: true
  },

  build: {
    //Template for index.html
    index: path.resolve(__dirname, '../dist/index.html'),

    //Paths
    assetsRoot: path.resolve(__dirname, '../dist'),
    assetsSubDirectory: 'static',
    assetsPublicPath: './',

    /**
     * Source Maps
     */
    productionSourceMap: false,
    devtool: 'eval-source-map',
    productionGzip: false,
    productionGzipExtensions: ['js', 'css'],

    // Run build with `--report` to see bundle analyzer report
    bundleAnalyzerReport: process.env.npm_config_report
  }
}

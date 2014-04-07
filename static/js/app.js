'use strict';

angular.module('d3', [])
  .factory('d3Service', ['$document', '$q', '$rootScope',
    function($document, $q, $rootScope) {
      var d = $q.defer();
      function onScriptLoad() {
        // Load client in the browser
        $rootScope.$apply(function() { d.resolve(window.d3); });
      }
      // Create a script tag with d3 as the source
      // and call our onScriptLoad callback when it
      // has been loaded
      var scriptTag = $document[0].createElement('script');
      scriptTag.type = 'text/javascript'; 
      scriptTag.async = true;
      scriptTag.src = 'http://d3js.org/d3.v3.min.js';
      scriptTag.onreadystatechange = function () {
        if (this.readyState == 'complete') onScriptLoad();
      }
      scriptTag.onload = onScriptLoad;

      var s = $document[0].getElementsByTagName('body')[0];
      s.appendChild(scriptTag);

      return {
        d3: function() { return d.promise; }
      };
    }
  ]);

// Declare app level module which depends on filters, and services
angular.module('sven', [
  'ngRoute',

  'sven.filters',
  'sven.services',
  'sven.directives',
  'sven.controllers',
  //'ngAnimate',
  
  'd3'
]).
config(['$routeProvider', '$httpProvider', function($routeProvider, $httpProvider, $cookies) {
  $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
  $httpProvider.defaults.xsrfCookieName = 'csrftoken';

  $routeProvider.when('/', {templateUrl: '/static/partials/corpus.list.html', controller: 'indexCtrl'});
  
  $routeProvider.when('/corpus/:id/documents', {templateUrl: '/static/partials/document.list.html', controller: 'documentListCtrl', reloadOnSearch:false});
  $routeProvider.when('/corpus/:id/segments', {templateUrl: '/static/partials/segment.list.html', controller: 'segmentListCtrl'});
  
  $routeProvider.when('/document/:id', {templateUrl: '/static/partials/document.html', controller: 'documentCtrl'});
  
  $routeProvider.when('/document', {templateUrl: '/static/partials/document.list.html', controller: 'MyCtrl2'});
  $routeProvider.when('/log', {templateUrl: '/static/partials/log.html', controller: 'logCtrl'});
  
  $routeProvider.otherwise({redirectTo: '/'});

  // warning/ error code given by my glue api
  $httpProvider.responseInterceptors.push(['$q', function($q) {
    return function(promise) {
      return promise.then(function(response) {
        response.data.extra = 'Interceptor strikes back';
        if(response.data.meta && response.data.meta.warnings){ // form error from server!
          // if(response.data.meta.warnings.invalid && response.data.meta.warnings.limit):
          // exceute, but send a message
          console.log('',response.data.meta.warnings);
          // return $q.reject(response);
        }
        return response; 
      }, function(response) { // The HTTP request was not successful.
        if (response.status === 401) {
          response.data = { 
            status: 'error', 
            description: 'Authentication required, or TIMEOUT session!'
          };
          return response;
        }
        return $q.reject(response);
      });
    };
  }]);
}]);
'use strict';
angular.module('sven', [
  'ngRoute',
  'sven.filters',
  'sven.services',
  'sven.directives',
  'sven.controllers',
  'ui.bootstrap',
  'monospaced.elastic',
  'sven.D3'
]).
config(['$routeProvider', '$httpProvider', function($routeProvider, $httpProvider, $cookies) {
  $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
  $httpProvider.defaults.xsrfCookieName = 'csrftoken';

  $routeProvider.when('/', {templateUrl: '/static/partials/index.html', controller: 'indexCtrl'});
  
  $routeProvider.when('/corpus/:id/documents', {templateUrl: '/static/partials/document.list.html', controller: 'documentListCtrl', reloadOnSearch:false});
  $routeProvider.when('/corpus/:id/segments', {templateUrl: '/static/partials/segment.list.html', controller: 'segmentListCtrl'});
  $routeProvider.when('/corpus/:corpus_id/document/new', {templateUrl: '/static/partials/document.new.html', controller: 'documentCtrl'});
  $routeProvider.when('/corpus/:corpus_id/monitor', {templateUrl: '/static/partials/monitor.html', controller: 'monitorCtrl'});
  
  $routeProvider.when('/document/:id', {templateUrl: '/static/partials/document.html', controller: 'documentCtrl'});
  
  $routeProvider.when('/document', {templateUrl: '/static/partials/document.list.html', controller: 'MyCtrl2'});
  
  $routeProvider.when('/profile', {templateUrl: '/static/partials/profile.html', controller: 'profileCtrl'});
  $routeProvider.when('/search', {templateUrl: '/static/partials/search.html', controller: 'searchCtrl'});


  $routeProvider.otherwise({redirectTo: '/'});

  // warning/ error code given by my glue api
  $httpProvider.responseInterceptors.push(['$q','$log', function($q, $log) {
    return function(promise) {
      return promise.then(function(response) {
        response.data.extra = 'Interceptor strikes back';
        if(response.data.meta && response.data.meta.warnings){ // form error from server!
          // if(response.data.meta.warnings.invalid && response.data.meta.warnings.limit):
          // exceute, but send a message
          $log.info('warnings',response.data.meta.warnings);
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
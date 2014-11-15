'use strict';

/**
 * @ngdoc overview
 * @name svenClientApp
 * @description
 * # svenClientApp
 *
 * Main module of the application.
 */
angular
  .module('svenClientApp', [
    'ngAnimate',
    'ngCookies',
    'ngResource',
    'ngRoute',
    'ngSanitize',
    'ngTouch',
    'ui.bootstrap',
    'angularFileUpload',
    'ngTagsInput'
  ])
  .config(function ($routeProvider, $httpProvider) {
    $routeProvider
      .when('/', {
        templateUrl: 'static/app/views/main.html',
        controller: 'MainCtrl'
      })
      .when('/about', {
        templateUrl: 'static/app/views/about.html',
        controller: 'AboutCtrl'
      })
      .when('/documents', {
        templateUrl: 'static/app/views/documents.html',
        controller: 'DocumentsCtrl'
      })
      .when('/documents/new', {
        templateUrl: 'static/app/views/documents.new.html',
        controller: 'DocumentsCtrl'
      })
      .when('/document/:id', { // document id
        templateUrl: 'static/app/views/document.html',
        controller: 'DocumentCtrl'
      })
      .when('/document/:id/edit', { // document id
        templateUrl: 'static/app/views/document.edit.html',
        controller: 'DocumentCtrl'
      })
      .when('/document/:id/text', { // document id
        templateUrl: 'static/app/views/document.text.html',
        controller: 'DocumentCtrl'
      })
      .when('/concepts', {
        templateUrl: 'static/app/views/concepts.html',
        controller: 'ConceptsCtrl'
      })
      .when('/concept', {
        templateUrl: 'static/app/views/concept.html',
        controller: 'ConceptCtrl'
      })
      .when('/profile', {
        templateUrl: 'static/app/views/profile.html',
        controller: 'ProfileCtrl'
      })
      .when('/corpus/:id', {
        templateUrl: 'static/app/views/corpus.html',
        controller: 'CorpusCtrl'
      })
      .when('/corpus/:id/concepts', {
        templateUrl: 'static/app/views/concepts.html',
        controller: 'ConceptsCtrl'
      })
      .when('/corpus/:id/documents', {
        templateUrl: 'static/app/views/documents.html',
        controller: 'CorpusDocumentsCtrl'
      })
      .when('/corpus/:id/documents/new', {
        templateUrl: 'static/app/views/documents.new.html',
        controller: 'CorpusDocumentsCtrl'
      })
      .when('/corpus/:id/stopwords', {
        templateUrl: 'static/app/views/stopwords.html',
        controller: 'StopwordsCtrl'
      })
      .when('/corpus/:id/search/:query', {
        templateUrl: 'static/app/views/search.html',
        controller: 'SearchCtrl'
      })
      .otherwise({
        redirectTo: '/'
      });

      $httpProvider.responseInterceptors.push(['$q','$log', function($q, $log) {
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';

        return function(promise) {
          return promise.then(function(response) {
            // response.data.extra = 'intercepted';
            if(response.data.status == 'error') {
              toast(response.data.error);
            }
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
  });


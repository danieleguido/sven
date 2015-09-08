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
  .module('sven', [
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
        templateUrl: SVEN_STATIC_URL + '/views/index.html',
        controller: 'IndexCtrl'
      })
      .when('/about', {
        templateUrl: SVEN_STATIC_URL + '/views/about.html',
        controller: 'AboutCtrl'
      })
      .when('/documents', {
        templateUrl: SVEN_STATIC_URL + '/views/documents.html',
        controller: 'DocumentsCtrl'
      })
      .when('/documents/new', {
        templateUrl: SVEN_STATIC_URL + '/views/documents.new.html',
        controller: 'DocumentsCtrl'
      })
      .when('/document/:id', { // document id
        templateUrl: SVEN_STATIC_URL + '/views/document.html',
        controller: 'DocumentCtrl',
        reloadOnSearch: false
      })
      .when('/document/:id/edit', { // document id
        templateUrl: SVEN_STATIC_URL + '/views/document.edit.html',
        controller: 'DocumentCtrl'
      })
      .when('/document/:id/text', { // document id
        templateUrl: SVEN_STATIC_URL + '/views/document.text.html',
        controller: 'DocumentCtrl'
      })
      .when('/concepts', {
        templateUrl: SVEN_STATIC_URL + '/views/concepts.html',
        controller: 'ConceptsCtrl'
      })
      .when('/concept', {
        templateUrl: SVEN_STATIC_URL + '/views/concept.html',
        controller: 'ConceptCtrl'
      })
      .when('/profile', {
        templateUrl: SVEN_STATIC_URL + '/views/profile.html',
        controller: 'ProfileCtrl'
      })
      .when('/corpus/:id', {
        templateUrl: SVEN_STATIC_URL + '/views/corpus.html',
        controller: 'CorpusCtrl'
      })
      .when('/corpus/:id/concepts', {
        templateUrl: SVEN_STATIC_URL + '/views/concepts.html',
        controller: 'ConceptsCtrl'
      })
      .when('/corpus/:id/timeline', {
        templateUrl: SVEN_STATIC_URL + '/views/stream.html',
        controller: 'StreamCtrl',
        reloadOnSearch: false,
        resolve: {
          concepts: function(CorpusVisFactory, $route) { // @todo:  CorpusVisFactory
            // http://localhost:8000/api/corpus/1/concept?filters=%7B%7D&group_by=tm&limit=50&offset=0&order_by=%5B%22-tf%22%5D
            return CorpusVisFactory.get({
              id: $route.current.params.id,
              vis:   'stream',
              model: 'concept'
            }).$promise;
          }
        }
      })
      .when('/corpus/:id/network', {
        templateUrl: SVEN_STATIC_URL + '/views/network.html',
        controller: 'NetworkCtrl',

        resolve: {
          graph: function(CorpusVisFactory, $route) {
            return CorpusVisFactory.get({
              id: $route.current.params.id,
              vis:   'graph',
              model: 'tags'
            }).$promise;
          }
        }
      })
      .when('/corpus/:id/coocc', {
        templateUrl: SVEN_STATIC_URL + '/views/network.html',
        controller: 'NetworkCtrl',
        reloadOnSearch: false,
        resolve: {
          graph: function(CorpusVisFactory, $route) {
            // load filters, if any are provided.
            // console.log('netword',$route.current.params)
            var filters = {};
            var between = $route.current.params.between;
            if(['document', 'concept', 'tag'].indexOf(between) == -1)
              between = 'concept';

            if($route.current.params.start)
              filters.date__gte=$route.current.params.start

            if($route.current.params.tag)
              filters.tags__slug=$route.current.params.tag

            if($route.current.params.end)
              filters.date__lte=$route.current.params.end
            
            return CorpusVisFactory.get(angular.extend({
              id: $route.current.params.id,
              vis:   'network',
              model: between
            }, {
              filters: JSON.stringify(filters)
            })).$promise;
          }
        }
      })
      .when('/corpus/:id/documents', {
        templateUrl: SVEN_STATIC_URL + '/views/documents.html',
        controller: 'CorpusDocumentsCtrl',
        reloadOnSearch: false
      })
      .when('/corpus/:id/documents/new', {
        templateUrl: SVEN_STATIC_URL + '/views/documents.new.html',
        controller: 'CorpusDocumentsCtrl'
      })
      .when('/corpus/:id/stopwords', {
        templateUrl: SVEN_STATIC_URL + '/views/stopwords.html',
        controller: 'StopwordsCtrl'
      })
      .when('/corpus/:id/search/:query', {
        templateUrl: SVEN_STATIC_URL + '/views/search.html',
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
            if(response.data.status == 'error') { // on error recieived other and 200 thhtp, reject response and sow the meaning
              if(response.data.code == 'FormErrors') {
                var msg = [];// the error message, concatenated 
                for (var i in response.data.error) {
                  msg.push('<b>' + i + '</b>: ' +  response.data.error[i].join('.'));
                }
                toast(msg.join('<br/>'), {stayTime: msg.length * 3000});
              } else if(response.data.code == 'BUSY') {
                toast(response.data.error, {stayTime: 3000});
              }
                
              $log.info('warnings',response);
              
              return $q.reject(response);
              
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


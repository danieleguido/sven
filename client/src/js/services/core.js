'use strict';

/**
 * @ngdoc service
 * @name svenClientApp.core
 * @description
 * # core
 * Factory in the svenClientApp.
 */
angular.module('sven')
  .factory('NotificationFactory', function($resource) {
    return $resource(SVEN_BASE_URL + '/api/notification', {}, {
        query: {method: 'GET', isArray: false },
    });
  })
   .factory('CommandFactory', function($resource) {
    return $resource(SVEN_BASE_URL + '/api/corpus/:id/start/:cmd', {}, {
        launch: {method: 'POST', params: {cmd: '@cmd', id:'@id'}}
    });
  })
  .factory('ProfileFactory', function($resource) {
    return $resource(SVEN_BASE_URL + '/api/profile', {}, {
        query: {method: 'GET', isArray: false },
        update: {method: 'POST', isArray: false }
    });
  })
  .factory('CorporaFactory', function($resource) {
    return $resource(SVEN_BASE_URL + '/api/corpus', {}, {
      save: {method: 'POST', isArray: false }
    });
  })
  .factory('CorpusFactory', function($resource) {
    return $resource(SVEN_BASE_URL + '/api/corpus/:id', {}, {
        query: {method: 'GET', isArray: false, params: {id:'@id'}},
        update: {method: 'POST', isArray: false, params: {id:'@id'} }
    });
  })
  .factory('CorpusFacetsFactory', function($resource) {
    return $resource(SVEN_BASE_URL + '/api/corpus/:id/filters', {}, {
        query: {method: 'GET', isArray: false, params: {id:'@id'}},
        update: {method: 'POST', isArray: false, params: {id:'@id'} }
    });
  })
  .factory('StopwordsFactory', function($resource) {
    return $resource(SVEN_BASE_URL + '/api/corpus/:id/stopwords', {}, {
        query: {method: 'GET', isArray: false, params: {id:'@id'}},
        save: {method: 'POST', isArray: false, params: {id:'@id'} }
    });
  });

  
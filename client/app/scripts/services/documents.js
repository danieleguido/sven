'use strict';

/**
 * @ngdoc service
 * @name svenClientApp.documents
 * @description
 * # documents
 * Factory in the svenClientApp.
 */
angular.module('svenClientApp')
  .factory('DocumentsFactory', function ($resource) {
    return $resource('/api/corpus/:id/document', {}, {
      query: {method: 'GET', isArray: false },
      save: {method: 'POST', params: {id: '@id'} },
    });
  })
  .factory('DocumentsConceptsFactory', function ($resource) {
    return $resource('/api/document/:id/segments', {}, {
      query: {method: 'GET', isArray: false,  params: {id: '@id'}  },
    });
  })
  .factory('DocumentTagsFactory', function($resource) {
    return $resource('/api/document/:id/tag', {}, {
      save: {method: 'POST', params: {id: '@id'} },
      remove: {method: 'DELETE', params: {id: '@id'} }
    });
    //test: http://localhost:9090/api/document/4/tag?indent&method=POST&type=ac&tags=ONG
  })
  .factory('DocumentFactory', function($resource) {
    return $resource('/api/document/:id', {}, {
      query: {method: 'GET', isArray: false, params: {id: '@id'} },
      save: {method: 'POST', isArray: false, params: {id: '@id'} },
      remove: {method: 'DELETE', params: {id: '@id'} }
    });
  })
  
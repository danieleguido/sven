'use strict';

/**
 * @ngdoc service
 * @name svenClientApp.concepts
 * @description
 * # concepts
 * Factory in the svenClientApp.
 */
angular.module('sven')
  .factory('ConceptsFactory', function($resource) {
    return $resource(SVEN_BASE_URL + '/api/corpus/:id/concept', {}, {
      query: {method: 'GET', isArray: false, params: {id: '@id'} },
      remove: {method: 'DELETE', params: {id: '@id'} }
    });
  });

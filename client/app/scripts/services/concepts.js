'use strict';

/**
 * @ngdoc service
 * @name svenClientApp.concepts
 * @description
 * # concepts
 * Factory in the svenClientApp.
 */
angular.module('svenClientApp')
  .factory('ConceptsFactory', function($resource) {
    return $resource('/api/corpus/:id/segment', {}, {
      query: {method: 'GET', isArray: false, params: {id: '@id'} },
      remove: {method: 'DELETE', params: {id: '@id'} }
    });
  });

'use strict';

/* Services */


// Demonstrate how to register services
// In this case it is a simple value service.
angular.module('sven.services', ['ngResource'])
  .factory('ProfileFactory', function($resource) {
    return $resource('/api/profile', {}, {
        query: { method: 'GET' },
        update: { method: 'POST' }
    });
  })
  .factory('CorpusListFactory', function($resource) {
    return $resource('/api/corpus', {}, {
        query: { method: 'GET', isArray: false },
        create: { method: 'POST' }
    });
  })
  .factory('CorpusFactory', function($resource) {
    return $resource('/api/corpus/:id', {}, {
        query: { method: 'GET', params: {id: '@id'}},
        update: { method: 'POST' }
    });
  })
  .factory('DocumentListFactory', function($resource) {
    return $resource('/api/corpus/:id/document', {}, {
        query: { method: 'GET', isArray: false },
        create: { method: 'POST' }
    });
  })
  .value('version', '0.1');
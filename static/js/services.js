'use strict';

/* Services */


// Demonstrate how to register services
// In this case it is a simple value service.
angular.module('sven.services', ['ngResource', ])//'ngAnimate'])
   .factory('NotificationFactory', function($resource) {
    return $resource('/api/notification', {}, {
        query: {method: 'GET' },
    });
  })
   .factory('CommandFactory', function($resource) {
    return $resource('/api/corpus/:id/start/:cmd', {}, {
        launch: {method: 'POST', params: {cmd: '@cmd', id:'@id'}}
    });
  })
  .factory('ProfileFactory', function($resource) {
    return $resource('/api/profile', {}, {
        query: {method: 'GET' },
        update: {method: 'POST' }
    });
  })
  .factory('CorpusListFactory', function($resource) {
    return $resource('/api/corpus', {}, {
        query: {method: 'GET', isArray: false },
        create: {method: 'POST' }
    });
  })
  .factory('CorpusFactory', function($resource) {
    return $resource('/api/corpus/:id', {}, {
        query: {method: 'GET', params: {id: '@id'}},
        update: {method: 'POST' }
    });
  })
  .factory('DocumentListFactory', function($resource) {
    return $resource('/api/corpus/:id/document', {}, {
        query: {method: 'GET', isArray: false },
        create: {method: 'POST' }
    });
  })
  .factory('DocumentFactory', function($resource) {
    return $resource('/api/document/:id', {}, {
        query: {method: 'GET', isArray: false, params: {id: '@id'} }
    });
  })
  .factory('DocumentSegmentsFactory', function($resource) {
    return $resource('/api/document/:id/segments', {}, {
        query: {method: 'GET', isArray: false, params: {id: '@id'} }
    });
  })
  .factory('SegmentListFactory', function($resource) { // that is the segments service for a GIVEN corpus!
    return $resource('/api/corpus/:id/segment', {}, {
      query: {method: 'GET', isArray: false, params: {id: '@id'} }
    });
  })
  .value('version', '0.1');
'use strict';

/**
 * @ngdoc service
 * @name svenClientApp.core
 * @description
 * # core
 * Factory in the svenClientApp.
 */
angular.module('svenClientApp')
  .factory('core', function () {
    // Service logic
    // ...

    var meaningOfLife = 42;

    // Public API here
    return {
      someMethod: function () {
        return meaningOfLife;
      }
    };
  })
  .factory('LoginFactory', function($resource) {
    return $resource('http://localhost:8000/api/login', {}, {
        query: {method: 'GET' },
    });
  })
  .factory('NotificationFactory', function($resource) {
    return $resource('http://localhost:8000/api/notification', {}, {
        query: {method: 'GET' },
    });
  })
   .factory('CommandFactory', function($resource) {
    return $resource('http://localhost:8000/api/corpus/:id/start/:cmd', {}, {
        launch: {method: 'POST', params: {cmd: '@cmd', id:'@id'}}
    });
  })
  .factory('ProfileFactory', function($resource) {
    return $resource('/api/profile', {}, {
        query: {method: 'GET' },
        update: {method: 'POST' }
    });
  })
  .factory('CorpusFactory', function($resource) {
    return $resource('/api/corpus/:id', {}, {
        query: {method: 'GET', params: {id:'@id'}},
        update: {method: 'POST', params: {id:'@id'} }
    });
  });

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
  /*
    sample toast function to enable message notification.
    It needs jquerytoastmessage jquery lib to work properly.
    Waiting for an angular version.
  */
  .factory('LoginFactory', function($resource) {
    return $resource(SVEN_BASE_URL + '/api/login', {}, {
        query: {method: 'GET' },
    });
  })
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

  .factory('StopwordsFactory', function($resource) {
    return $resource(SVEN_BASE_URL + '/api/corpus/:id/stopwords', {}, {
        query: {method: 'GET', isArray: false, params: {id:'@id'}},
        save: {method: 'POST', isArray: false, params: {id:'@id'} }
    });
  });

  
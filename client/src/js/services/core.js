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
  .factory('CorpusRelatedFactory', function($resource) {
    return $resource(SVEN_BASE_URL + '/api/corpus/:id/related/:related_model/:related_id');
  })
  .factory('StopwordsFactory', function($resource) {
    return $resource(SVEN_BASE_URL + '/api/corpus/:id/stopwords', {}, {
        query: {method: 'GET', isArray: false, params: {id:'@id'}},
        save: {method: 'POST', isArray: false, params: {id:'@id'} }
    });
  })
  .factory('CorpusVisFactory', function($resource) {
    return $resource(SVEN_BASE_URL + '/api/:vis/corpus/:id/:model');
  })

  .factory('djangoInterceptor', function($q, $log) {
    return {
      // request: function (config) {
      //     return config || $q.when(config);
      // },
      // requestError: function(request){
      //     return $q.reject(request);
      // },
      response: function (response) {
        if(response && response.data && response.data.status)
          response.data.intercepted = true;
        if(response && response.data.status == 'error') { // on error recieived other and 200 thhtp, reject response and sow the meaning
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
        if(response && response.data.meta && response.data.meta.warnings){ // form error from server!
          // if(response.data.meta.warnings.invalid && response.data.meta.warnings.limit):
          // exceute, but send a message
          $log.info('warnings',response.data.meta.warnings);
          // return $q.reject(response);
        }

        return response || $q.when(response);
      },
      responseError: function (response) {
        if (response.status === 401) {
          response.data = { 
            status: 'error', 
            description: 'Authentication required, or TIMEOUT session!'
          };
          return response;
        }
        return $q.reject(response);
      }
    };
  })

  
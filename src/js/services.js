'use strict';

/* Services */


// Demonstrate how to register services
// In this case it is a simple value service.
angular.module('sven.services', ['ngResource', ])//'ngAnimate'])
  /*
    sample toast function to enable message notification.
    It needs jquerytoastmessage jquery lib to work properly.
    Waiting for an angular version.
  */
  .factory('ToastFactory', function() {
    return {
      toast: function(message, title, options){
        if(!options){
          options={}
        };
        if(typeof title=="object"){
          options=title;
          title=undefined;
        }

        if(options.cleanup!=undefined)
          $().toastmessage("cleanToast");
        var settings=$.extend({
          text: "<div>"+(!title?"<h1>"+message+"</h1>":"<h1>"+title+"</h1><p>"+message+"</p>")+"</div>",
          type: "notice",
          position: "bottom-right",
          inEffectDuration: 200,
          outEffectDuration: 200,
          stayTime: 1900
        },options);

        $().toastmessage("showToast", settings);
      }
    };
  })
  .factory('D3Factory', function($resource) {
    return $resource('/api/d3/:vis', {}, { // vi can be timeline|
        timeline: {method: 'GET', params: {vis: 'timeline'}},
    });
  })
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
        save: {method: 'POST', params: {id: '@id'} }
    });
  })
  .factory('DocumentFactory', function($resource) {
    return $resource('/api/document/:id', {}, {
        query: {method: 'GET', isArray: false, params: {id: '@id'} }
    });
  })
  .factory('DocumentTagsFactory', function($resource) {
    return $resource('/api/document/:id/tag', {}, {
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
  .factory('SegmentFactory', function($resource) { // that is the segments service for a GIVEN corpus!
    return $resource('/api/corpus/:corpus_id/segment/:segment_id', {}, {
      query: {method: 'GET', isArray: false, params: {corpus_id: '@corpus_id', segment_id: '@segment_id', } }
    });
  })
  .factory('TagListFactory', function($resource) { // that is the segments service for a GIVEN corpus!
    return $resource('/api/tag', {}, {
      query: {method: 'GET', isArray: false}
    });
  })
  .value('version', '0.2');
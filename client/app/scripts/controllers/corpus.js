'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:CorpusCtrl
 * @description
 * # CorpusCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('CorpusCtrl', function ($scope, $log, $routeParams, CorpusFactory) {
    $log.debug('CorpusCtrl ready ca');
    
    $scope.localCorpus = {};

    CorpusFactory.query({id: $routeParams.id}, function(data) {
      console.log(data)
      $scope.$parent.diffclone($scope.localCorpus, data.object);
    })
    
    $scope.$watch('corpora', function(){// pseudo react diff. looking for the local corpus among different corpora
      for(var i=0; i<$scope.$parent.corpora.length; i++) {
        if($scope.$parent.corpora[i].id == $routeParams.id) {
          $scope.$parent.diffclone($scope.localCorpus, $scope.$parent.corpora[i])
        }
      }
    });

  })
  .controller('CorpusDocumentsCtrl', function ($scope, $log, $location, $routeParams, DocumentsFactory) {
    $log.debug('CorpusDocumentsCtrl ready');
    

    DocumentsFactory.query({id:$routeParams.id}, function(data){
      $log.info('loading documents', data);
      $scope.items = data.objects;
      }, function(){
    });

    $scope.saveUrl = function() {
      $log.info('saveUrl: ', $scope.document.url);
      DocumentsFactory.save({
        id: $routeParams.id
      },{
        mimetype: 'text/html',
        name: $scope.document.url
          .replace(/http:\/\/w+/g,'')
          .replace(/[^\w]/g, ' ')
          .replace(/\s+/g,' ')
          .trim().substring(0,64),
        url:$scope.document.url
      }, function(data) {
        console.log(data);
        data.object && $location.path('/document/' + data.object.id);
      });
    };

    

  });

'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:StopwordsCtrl
 * @description
 * # StopwordsCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('StopwordsCtrl', function ($scope, $routeParams, $log, StopwordsFactory) {
    $scope.stopwords = [];
    $scope.localCorpus = {};
    
    StopwordsFactory.query({id:$routeParams.id}, function(data){
      $log.info('loading documents', data);
      $scope.stopwords = data.objects.join("\n");
      }, function(){
    });

    
    
    $scope.$watch('corpora', function(){// pseudo react diff. looking for the local corpus among different corpora
      for(var i=0; i<$scope.$parent.corpora.length; i++) {
        if($scope.$parent.corpora[i].id == $routeParams.id) {
          $scope.$parent.diffclone($scope.localCorpus, $scope.$parent.corpora[i])
        }
      }
    });
  });

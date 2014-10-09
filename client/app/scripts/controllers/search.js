'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:SearchCtrl
 * @description
 * # SearchCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('SearchCtrl', function ($scope, $log, $routeParams, DocumentsFactory) {
    $log.debug('SearchCtrl ready ca');
    
    $scope.localCorpus = {};
    
    $scope.$watch('corpora', function(){// pseudo react diff. looking for the local corpus among different corpora
      for(var i=0; i<$scope.$parent.corpora.length; i++) {
        if($scope.$parent.corpora[i].id == $routeParams.id) {
          $scope.$parent.diffclone($scope.localCorpus, $scope.$parent.corpora[i])
        }
      }
    });

    $scope.query = $routeParams.query;
    
    $scope.query && DocumentsFactory.query({id:$routeParams.id, search:$scope.query},{search:$scope.query}, function(data){
      console.log(data);
      $scope.items = data.objects;
    });

  });

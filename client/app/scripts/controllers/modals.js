'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:StopwordsCtrl
 * @description
 * # ModalTagCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('AttachTagCtrl', function ($scope, $modalInstance, item) {
    $scope.item = item;

    $scope.ok = function () {
      $modalInstance.close();
    };

    $scope.cancel = function () {
      $modalInstance.dismiss('cancel');
    };
  })


  .controller('AddCorpusCtrl', function ($scope, $log, $modalInstance, CorporaFactory) {
    $log.debug('AddCorpusCtrl is ready');
    
    $scope.ok = function () {
      CorporaFactory.save({name: $scope.candidate}, function () {
        $log.debug('AddCorpusCtrl --> corpus saved', $scope.$parent);
        toast('saving corpus ...', {stayTime: 5000});
      })
      $modalInstance.close();
    };

    $scope.cancel = function () {
      $modalInstance.dismiss('cancel');
    };
  })
  /*
    Event receiver and Modal windows redispatcher
  */
  .controller('ModalCtrl', function ($scope, $log, $modal) {
    $log.debug('ModalCtrl is ready');
    $scope.$on(OPEN_ADD_CORPUS, function () {
      $log.debug('opening add corpus modal');
      $modal.open({
        templateUrl: 'addCorpus.html',
        controller: 'AddCorpusCtrl',
        backdrop: false,
        size: 'sm',
      });
    });


  })

  .controller('ModalTagCtrl', function ($scope, $routeParams, $log, $modal) {
    

    var attachtag;

    $scope.$on(OPEN_ATTACH_TAG, function(e,doc) {
      attachtag = $modal.open({
        templateUrl: 'myModalContent.html',
        controller: 'AttachTagCtrl',
        backdrop:false,
        size: 'sm',
        resolve: {
          item: function () {
            return doc;
          }
        }
      });
    });
  })


  .controller('PreviewTsvCtrl', function ($scope, $modalInstance, table) {
    $scope.table = table;

    $scope.ok = function () {
      $modalInstance.close();
      $scope.onMetadataStart();
    };

    $scope.cancel = function () {
      $modalInstance.dismiss('cancel');
    };
  })
  .controller('ModalPreviewTsvCtrl', function ($scope, $filter, $routeParams, $log, $modal) {
    var modal;

    $scope.$watch('tsv', function(tsv) {
      if(!tsv)
        return;
      modal = $modal.open({
        templateUrl: 'previewTsv.html',
        controller: 'PreviewTsvCtrl',
        backdrop:false,
        resolve: {
          table: function () {
            console.log()
            return $filter('tsv')(tsv);
          }
        }
      });
    });
  })
  ;
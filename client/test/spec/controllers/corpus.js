'use strict';

describe('Controller: CorpusCtrl', function () {

  // load the controller's module
  beforeEach(module('svenClientApp'));

  var CorpusCtrl,
    scope;

  // Initialize the controller and a mock scope
  beforeEach(inject(function ($controller, $rootScope) {
    scope = $rootScope.$new();
    CorpusCtrl = $controller('CorpusCtrl', {
      $scope: scope
    });
  }));

  it('should attach a list of awesomeThings to the scope', function () {
    expect(scope.awesomeThings.length).toBe(3);
  });
});
